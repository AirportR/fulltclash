package main

//#include <stdlib.h>
import "C"
import (
	"context"
	"crypto/tls"
	"crypto/x509"
	_ "embed"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/Dreamacro/clash/adapter"
	"github.com/Dreamacro/clash/adapter/inbound"
	N "github.com/Dreamacro/clash/common/net"
	"github.com/Dreamacro/clash/common/pool"
	"github.com/Dreamacro/clash/component/nat"
	"github.com/Dreamacro/clash/component/resolver"
	"github.com/Dreamacro/clash/constant"
	icontext "github.com/Dreamacro/clash/context"
	"github.com/Dreamacro/clash/listener/mixed"
	"github.com/Dreamacro/clash/listener/socks"
	"github.com/Dreamacro/clash/tunnel/statistic"
	"gopkg.in/yaml.v3"
	"io"
	"net"
	"net/http"
	"net/http/httptrace"
	"net/netip"
	"net/url"
	"os"
	"os/signal"
	"runtime"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

func main() {
	//startclashMixed(C.CString("127.0.0.1:1111"), 1)
}

//go:embed rootCA.crt
var FullTClashRootCa []byte
var rawcfgs = make([]*RawConfig, 128)
var (
	//tcpQueue = make(chan constant.ConnContext, 512)
	//udpQueue = make(chan *inbound.PacketAdapter, 512)
	//mixedListener  *mixed.Listener
	//mixedUDPLister *socks.UDPListener
	natTable   = nat.New()
	udpTimeout = 60 * time.Second
	// lock for recreate function
	mixedMux sync.Mutex
)

type RawConfig struct {
	Proxy map[string]any `yaml:"proxies"`
}

//export myURLTest
func myURLTest(URL *C.char, index int) uint16 {
	proxy, err := adapter.ParseProxy(rawcfgs[index].Proxy)
	if err != nil {
		fmt.Printf("error: %s \n", err.Error())
		return 0
	}
	_, meanDelay, err := proxy.URLTest(context.Background(), C.GoString(URL))
	if err != nil {
		fmt.Printf("error: %s \n", err.Error())
		return meanDelay
	}
	return meanDelay
}
func startclash(addr *C.char, index int) {
	in := make(chan constant.ConnContext, 500)
	defer close(in)

	l, err := socks.New(C.GoString(addr), in)
	if err != nil {
		panic(err)
	}
	defer l.Close()

	println("listen at:", l.Address())

	for c := range in {
		conn := c
		metadata := conn.Metadata()

		proxy, err := adapter.ParseProxy(rawcfgs[index].Proxy)

		if err != nil {
			fmt.Printf("error: %s \n", err.Error())
		}
		fmt.Printf("request incoming from %s to %s, using %s , index: %d\n", metadata.SourceAddress(), metadata.RemoteAddress(), proxy.Name(), index)
		go func() {
			remote, err := proxy.DialContext(context.Background(), metadata)
			if err != nil {
				fmt.Printf("dial error: %s\n", err.Error())
				return
			}
			relay(remote, conn.Conn())
		}()
	}
}

//export startclashMixed
func startclashMixed(rawaddr *C.char, index int) {
	addr := C.GoString(rawaddr)
	tcpQueue := make(chan constant.ConnContext, 256)
	udpQueue := make(chan *inbound.PacketAdapter, 32)
	mixedListener, mixedUDPLister := ReCreateMixed(addr, tcpQueue, udpQueue, index)
	defer mixedListener.Close()
	defer mixedUDPLister.Close()
	if index == 0 {
		numUDPWorkers := 4
		if num := runtime.GOMAXPROCS(0); num > numUDPWorkers {
			numUDPWorkers = num
		}
		for i := 0; i < numUDPWorkers; i++ {
			go func() {
				for conn1 := range udpQueue {
					handleUDPConn(conn1, index)
				}
			}()
		}
	}
	for conn2 := range tcpQueue {
		go handleTCPConn(conn2, index)
	}
}
func ReCreateMixed(rawaddr string, tcpIn chan<- constant.ConnContext, udpIn chan<- *inbound.PacketAdapter, index int) (*mixed.Listener, *socks.UDPListener) {
	addr := rawaddr
	mixedMux.Lock()
	defer mixedMux.Unlock()

	var err error
	defer func() {
		if err != nil {
			fmt.Printf("Start Mixed(http+socks) server error: %s\n", err.Error())
		}
	}()

	mixedListener, err := mixed.New(addr, tcpIn)
	if err != nil {
		return nil, nil
	}
	var mixedUDPLister *socks.UDPListener
	if index == 0 {
		mixedUDPLister, err = socks.NewUDP(addr, udpIn)
		if err != nil {
			return nil, nil
		}
	}

	fmt.Printf("Mixed(http+socks) proxy listening at: %s\n", mixedListener.Address())
	return mixedListener, mixedUDPLister
}

//	func processUDP(index int) {
//		queue := udpQueue
//		for conn := range queue {
//			handleUDPConn(conn, index)
//		}
//	}
func handleUDPConn(packet *inbound.PacketAdapter, index int) {
	metadata := packet.Metadata()
	if !metadata.Valid() {
		fmt.Printf("[Metadata] not valid: %#v", metadata)
		return
	}

	// make a fAddr if request ip is fakeip
	var fAddr netip.Addr
	if resolver.IsExistFakeIP(metadata.DstIP) {
		fAddr, _ = netip.AddrFromSlice(metadata.DstIP)
		fAddr = fAddr.Unmap()
	}

	// local resolve UDP dns
	if !metadata.Resolved() {
		ips, err := resolver.LookupIP(context.Background(), metadata.Host)
		if err != nil {
			return
		} else if len(ips) == 0 {
			return
		}
		metadata.DstIP = ips[0]
	}

	key := packet.LocalAddr().String()

	handle := func() bool {
		pc := natTable.Get(key)
		if pc != nil {
			err := handleUDPToRemote(packet, pc, metadata)
			if err != nil {
				return false
			}
			return true
		}
		return false
	}

	if handle() {
		return
	}

	lockKey := key + "-lock"
	cond, loaded := natTable.GetOrCreateLock(lockKey)

	go func() {
		if loaded {
			cond.L.Lock()
			cond.Wait()
			handle()
			cond.L.Unlock()
			return
		}

		defer func() {
			natTable.Delete(lockKey)
			cond.Broadcast()
		}()

		pCtx := icontext.NewPacketConnContext(metadata)
		proxy, err := adapter.ParseProxy(rawcfgs[index].Proxy)
		//proxy, rule, err := resolveMetadata(pCtx, metadata)
		if err != nil {
			fmt.Printf("[UDP] Parse metadata failed: %s", err.Error())
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), constant.DefaultUDPTimeout)
		defer cancel()
		rawPc, err := proxy.ListenPacketContext(ctx, metadata.Pure())
		if err != nil {
			fmt.Printf(
				"[UDP] dial %s %s --> %s error: %s",
				proxy.Name(),
				metadata.SourceAddress(),
				metadata.RemoteAddress(),
				err.Error(),
			)
			return
		}
		pCtx.InjectPacketConn(rawPc)
		pc := statistic.NewUDPTracker(rawPc, statistic.DefaultManager, metadata, nil)

		oAddr, _ := netip.AddrFromSlice(metadata.DstIP)
		oAddr = oAddr.Unmap()
		go handleUDPToLocal(packet.UDPPacket, pc, key, oAddr, fAddr)

		natTable.Set(key, pc)
		handle()
	}()
}
func handleUDPToLocal(packet constant.UDPPacket, pc net.PacketConn, key string, oAddr, fAddr netip.Addr) {
	buf := pool.Get(pool.UDPBufferSize)
	defer pool.Put(buf)
	defer natTable.Delete(key)
	defer pc.Close()

	for {
		err := pc.SetReadDeadline(time.Now().Add(udpTimeout))
		if err != nil {
			return
		}
		n, from, err := pc.ReadFrom(buf)
		if err != nil {
			return
		}

		fromUDPAddr := from.(*net.UDPAddr)
		if fAddr.IsValid() {
			fromAddr, _ := netip.AddrFromSlice(fromUDPAddr.IP)
			fromAddr = fromAddr.Unmap()
			if oAddr == fromAddr {
				fromUDPAddr.IP = fAddr.AsSlice()
			}
		}

		_, err = packet.WriteBack(buf[:n], fromUDPAddr)
		if err != nil {
			return
		}
	}
}
func handleUDPToRemote(packet constant.UDPPacket, pc constant.PacketConn, metadata *constant.Metadata) error {
	defer packet.Drop()

	addr := metadata.UDPAddr()
	if addr == nil {
		return errors.New("udp addr invalid")
	}

	if _, err := pc.WriteTo(packet.Data(), addr); err != nil {
		return err
	}
	// reset timeout
	err := pc.SetReadDeadline(time.Now().Add(udpTimeout))
	if err != nil {
		return err
	}

	return nil
}
func handleTCPConn(connCtx constant.ConnContext, index int) {
	metadata := connCtx.Metadata()
	proxy, err := adapter.ParseProxy(rawcfgs[index].Proxy)
	if err != nil {
		fmt.Printf("error: %s \n", err.Error())
	}
	fmt.Printf("request incoming from %s to %s, using %s , index: %d\n", metadata.SourceAddress(), metadata.RemoteAddress(), proxy.Name(), index)
	ctx, cancel := context.WithTimeout(context.Background(), constant.DefaultTCPTimeout)
	defer cancel()
	remoteConn, err := proxy.DialContext(ctx, metadata)
	if err != nil {
		fmt.Printf(
			"[TCP] dial %s %s --> %s error: %s",
			proxy.Name(),
			metadata.SourceAddress(),
			metadata.RemoteAddress(),
			err.Error(),
		)
		return
	}
	defer remoteConn.Close()
	N.Relay(connCtx.Conn(), remoteConn)
}

//export myclash
func myclash(addr *C.char, index int) {
	go startclash(addr, index)
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
}

//export myclash2
func myclash2(addr *C.char, index int) {
	go startclashMixed(addr, index)
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
}

func relay(l, r net.Conn) {
	go func() {
		_, err := io.Copy(l, r)
		if err != nil {

		}
	}()
	_, err := io.Copy(r, l)
	if err != nil {
		return
	}
}

//export setProxy
func setProxy(oldstr *C.char, index int) int8 {
	if index > 128 {
		fmt.Printf("setProxy index must be less than 65, current index is %d", index)
		return 1
	}
	if len(rawcfgs) < 128 {
		fmt.Println("init rawconfigs")
		for i := 0; i < 128; i++ {
			rawcfgs = append(rawcfgs, &RawConfig{Proxy: map[string]any{}})
		}
	}
	str := C.GoString(oldstr)
	err := yaml.Unmarshal([]byte(str), &rawcfgs[index])
	if err != nil {
		errstr := err.Error()
		fmt.Printf("setproxy error: %s\n", errstr)
		return 1
	}
	//go startclash()
	return 0
}

//export stop
func stop(flag int) {
	if flag > 0 {
		os.Exit(1)
	}
}

//export freeMe
func freeMe(data *C.char) {
	C.free(unsafe.Pointer(data))
}

//export urlTest
func urlTest(rawurl *C.char, index int, timeout int) (uint16, uint16, error) {
	ctx := context.Background()
	newurl := C.GoString(rawurl)
	proxy, err := adapter.ParseProxy(rawcfgs[index].Proxy)

	if err != nil {
		return 0, 0, err
	}

	addr, err := urlToMetadata(newurl)
	if err != nil {
		return 0, 0, err
	}

	instance, err := proxy.DialContext(ctx, &addr)
	if err != nil {
		return 0, 0, err
	}
	defer instance.Close()

	transport := &http.Transport{
		DialContext: func(ctx context.Context, network string, addr string) (net.Conn, error) { return instance, nil },
		//Dial: func(network, addr string) (net.Conn, error) { return instance, nil },
		// from http.DefaultTransport
		MaxIdleConns:          100,
		IdleConnTimeout:       3 * time.Second,
		TLSHandshakeTimeout:   time.Duration(timeout) * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: false,
			// for version prior to tls1.3, the handshake will take 2-RTTs,
			// plus, majority server supports tls1.3, so we set a limit here
			MinVersion: tls.VersionTLS13,
			RootCAs:    rootCAPrepare(),
		},
	}

	req, err := http.NewRequest("GET", newurl, nil)
	if err != nil {
		return 0, 0, err
	}

	tlsStart := int64(0)
	tlsEnd := int64(0)
	writeStart := int64(0)
	writeEnd := int64(0)
	trace := &httptrace.ClientTrace{
		TLSHandshakeStart: func() {
			tlsStart = time.Now().UnixMilli()
		},
		TLSHandshakeDone: func(cs tls.ConnectionState, err error) {
			tlsEnd = time.Now().UnixMilli()
			if err != nil {
				tlsEnd = 0
			}
		},
		GotFirstResponseByte: func() {
			writeEnd = time.Now().UnixMilli()
		},
		WroteHeaders: func() {
			writeStart = time.Now().UnixMilli()
		},
	}
	req = req.WithContext(httptrace.WithClientTrace(req.Context(), trace))

	connStart := time.Now().UnixMilli()
	if resp, err := transport.RoundTrip(req); err != nil {
		return 0, 0, err
	} else {
		if !strings.HasPrefix(newurl, "https:") {
			return uint16(writeStart - connStart), uint16(writeEnd - connStart), nil
		}
		if resp.TLS != nil && resp.TLS.HandshakeComplete {
			connEnd := time.Now().UnixMilli()
			fmt.Printf("Urltest end. Name:%s, TimeStack:%d,%d,%d,%d\n", proxy.Name(), connEnd-writeEnd, writeEnd-tlsEnd, tlsEnd-tlsStart, tlsStart-connStart)
			// use payload rtt
			return uint16(writeEnd - tlsEnd), uint16(writeEnd - connStart), nil
			// return uint16(tlsEnd - tlsStart), uint16(writeEnd - connStart), nil
		}
		return 0, 0, fmt.Errorf("cannot extract payload from response")
	}
}

//export urltestJson
func urltestJson(url *C.char, index int, timeout int) *C.char {
	retMap := make(map[string]interface{})
	rtt, delay, err := urlTest(url, index, timeout)
	if err != nil {

	}
	retMap["rtt"] = rtt
	retMap["delay"] = delay
	retMap["err"] = err
	ret, _ := json.Marshal(retMap)
	return C.CString(string(ret))
}

func rootCAPrepare() *x509.CertPool {
	rootCAs := x509.NewCertPool()
	rootCAs.AppendCertsFromPEM(FullTClashRootCa)
	return rootCAs
}
func urlToMetadata(rawURL string) (addr constant.Metadata, err error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return
	}

	port := u.Port()
	if port == "" {
		switch u.Scheme {
		case "https":
			port = "443"
		case "http":
			port = "80"
		default:
			err = fmt.Errorf("%s scheme not Support", rawURL)
			return
		}
	}

	addr = constant.Metadata{
		Host:    u.Hostname(),
		DstIP:   nil,
		DstPort: port,
	}
	return
}
