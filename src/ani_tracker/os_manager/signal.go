package os_manager

import (
	"log"
	"os"
	"os/signal"
	"syscall"
)

func CatchTerminateSignal(stop chan<- struct{}) {
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigs
		log.Println("Terminate signal received, cleaning up...")
		close(stop)
	}()
}
