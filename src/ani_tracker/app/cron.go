package app

import (
	"ani-tracker/os_manager"
	"log"
	"time"

	"github.com/fsnotify/fsnotify"
)

type CronJob struct {
	Interval          time.Duration
	Job               func() error
	Attempt           int
	BackoffMultiplier time.Duration // Retry time of cronjobs = Attempt * BackoffMultiplier
	Stop              chan struct{}
	LockFile          *os_manager.LockFile
}

func (cj *CronJob) printNextRun() {
	log.Printf("Next run is scheduled at: %s",
		time.Now().Add(cj.Interval).Format("2006/01/02 15:04:05"))
}

func (cj *CronJob) lockFileWatcher() error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}

	if err := watcher.Add(cj.LockFile.FilePath); err != nil {
		watcher.Close()
		return err
	}

	go func() {
		defer watcher.Close()
		for {
			select {
			case event := <-watcher.Events:
				if event.Op&fsnotify.Remove != 0 {
					log.Println("Lock file removed, exiting cron...")
					select {
					case <-cj.Stop:
						// already closed
					default:
						close(cj.Stop)
					}
				}
			case err := <-watcher.Errors:
				log.Println("Watcher error:", err)
			case <-cj.Stop:
				return
			}
		}
	}()

	return nil
}

func (cj *CronJob) Runner() error {
	if err := cj.lockFileWatcher(); err != nil {
		return err
	}

	log.Println("Program is running in background")
	cj.printNextRun()

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

func (cj *CronJob) isStopped() bool {
	select {
	case <-cj.Stop:
		return true
	default:
		return false
	}
}

func (cj *CronJob) backoffSleep(backoff time.Duration) {
	for slept := time.Duration(0); slept < backoff; slept += time.Second {
		if cj.isStopped() {
			log.Println("Stop signal received during backoff, exiting cronjob")
			return
		}
		time.Sleep(time.Second)
	}
}

func (cj *CronJob) Run() {
	for attempt := 0; attempt < cj.Attempt; attempt++ {
		if cj.isStopped() {
			log.Println("Stop signal received before attempt, exiting cronjob")
			return
		}

		err := cj.Runner()
		if err != nil {
			if cj.isStopped() {
				log.Println("Cronjob stopped, not retrying")
				return
			}

			backoff := time.Duration(attempt+1) * time.Duration(cj.BackoffMultiplier)
			log.Printf("Cronjob attempt %d failed: %v. Retrying in %s...", attempt+1, err, backoff)

			cj.backoffSleep(backoff)

			continue
		}

		log.Println("Cronjob completed successfully")
		return
	}
	log.Println("All cronjob attempts failed")
}
