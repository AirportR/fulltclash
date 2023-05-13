package main

//#include <stdlib.h>
import "C"
import (
	"context"
	"crypto/tls"
	"crypto/x509"
	_ "embed"
	"encoding/json"
	"fmt"
	"github.com/Dreamacro/clash/adapter"
	"github.com/Dreamacro/clash/constant"
	"github.com/Dreamacro/clash/listener/socks"
	"gopkg.in/yaml.v3"
	"io"
	"net"
	"net/http"
	"net/http/httptrace"
	"net/url"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

//go:embed rootCA.crt
var FullTClashRootCa []byte

func main() {

}

type RawConfig struct {
	Proxy map[string]any `yaml:"proxies"`
}

var rawcfgs = make([]*RawConfig, 128)
var stoped = false

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
		if stoped {
			fmt.Printf("开始关闭通道")
			err := l.Close()
			if err != nil {
				return
			}
			break
		}
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

var listener = make([]*socks.Listener, 128)

//export closeclash
func closeclash(index int) {
	l := &listener[index]
	err := (*l).Close()
	if err != nil {
		panic(err)
	}
	//} else {
	//	fmt.Printf("The sock listening port has been successfully closed. index: %d\n", index)
	//}
}

//export startclash2
func startclash2(addr *C.char, index int) {
	in := make(chan constant.ConnContext, 512)
	defer close(in)

	l, err := socks.New(C.GoString(addr), in)
	if err != nil {
		panic(err)
	}
	defer l.Close()

	println("listen at:", l.Address())
	listener[index] = l

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
	fmt.Println("我到达末尾啦")
}

//export myclash
func myclash(addr *C.char, index int) {
	go startclash(addr, index)
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
}

//export sendsinal
func sendsinal() {
	pid := os.Getpid()
	fmt.Printf("当前进程PID: %d\n", pid)
	proc, err := os.FindProcess(pid)
	if err != nil {
		fmt.Println(err)
		return
	}
	err = proc.Kill()
	if err != nil {
		fmt.Println(err)
		return
	}

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
func setProxy(oldstr *C.char, index int) *C.char {
	if index > 128 {
		fmt.Printf("setProxy index must be less than 65, current index is %d", index)
		errtext := "setProxy index must be less than 129, current index is " + strconv.Itoa(index)
		return C.CString(errtext)
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
		return C.CString(errstr)
	}
	//go startclash()
	return C.CString("")
}

//export stop
func stop(flag int) {
	if flag > 0 {
		os.Exit(1)
	} else {
		stoped = false
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
