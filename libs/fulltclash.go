package main

import (
	"C"
	"context"
	"fmt"
	"github.com/Dreamacro/clash/adapter"
	"github.com/Dreamacro/clash/constant"
	"github.com/Dreamacro/clash/listener/socks"
	"gopkg.in/yaml.v3"
	"io"
	"net"
	"os"
	"os/signal"
	"strconv"
	"syscall"
)

func main() {
	myclash(C.CString("127.0.0.1:1114"), 0)
}

type RawConfig struct {
	Proxy map[string]any `yaml:"proxies"`
}

var rawcfgs = make([]*RawConfig, 64)
var stoped = false

func startclash(addr *C.char, index int) {
	in := make(chan constant.ConnContext, 100)
	defer close(in)

	l, err := socks.New(C.GoString(addr), in)
	if err != nil {
		panic(err)
	}
	defer func(l *socks.Listener) {
		err := l.Close()
		if err != nil {

		}
	}(l)

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

//export myclash
func myclash(addr *C.char, index int) {
	go startclash(addr, index)
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
func setProxy(oldstr *C.char, index int) *C.char {
	if index > 64 {
		fmt.Printf("setProxy index must be less than 65, current index is %d", index)
		errtext := "setProxy index must be less than 65, current index is " + strconv.Itoa(index)
		return C.CString(errtext)
	}
	if len(rawcfgs) < 64 {
		fmt.Println("初始化")
		for i := 0; i < 64; i++ {
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
