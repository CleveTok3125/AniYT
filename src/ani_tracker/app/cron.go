package app

import (
	"ani-tracker/os_manager"
	"log"
	"time"

	"github.com/fsnotify/fsnotify"
)

type CronJob struct {
	Interval time.Duration
	Job      func() error
	Stop     chan struct{}
	LockFile *os_manager.LockFile
}

func (cj *CronJob) printNextRun() {
	log.Printf("Next run is scheduled at: %s",
		time.Now().Add(cj.Interval).Format("2006/01/02 15:04:05"))
}

func (cj *CronJob) Run() error {
	log.Println("Program is running in background")
	cj.printNextRun()

	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	defer watcher.Close()

	if err := watcher.Add(cj.LockFile.FilePath); err != nil {
		return err
	}

	go func() {
		for {
			select {
			case event := <-watcher.Events:
				if event.Op&fsnotify.Remove != 0 {
					log.Println("Lock file removed, exiting cron...")
					close(cj.Stop)
					return
				}
			case err := <-watcher.Errors:
				log.Println("Watcher error:", err)
			case <-cj.Stop:
				return
			}
		}
	}()

	ticker := time.NewTicker(cj.Interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			log.Println("Running job...")

			if err := cj.Job(); err != nil {
				log.Printf("Job failed, stopping cron: %v", err)
				return err
			}

			cj.printNextRun()
		case <-cj.Stop:
			log.Println("Stop channel closed, exiting cron...")
			return nil
		}
	}
}
