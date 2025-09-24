package main

import (
	"log"
	"os"
	"time"
)

func cronJob(interval time.Duration, job func() error, stop <-chan struct{}) error {
	log.Println("Program is running in background")
	log.Printf("Next run at: %s",
		   time.Now().Add(interval).Format("2006/01/02 15:04:05"))

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
			case <-ticker.C:
				if _, err := os.Stat(lockFile); os.IsNotExist(err) {
					log.Println("Stop signal received, exiting...")
					return err
				}

				log.Println("Running...")

				if err := job(); err != nil {
					log.Printf("Job failed, stopping cron: %v", err)
					return err
				}

				log.Printf("Next run at: %s",
					   time.Now().Add(interval).Format("2006/01/02 15:04:05"))
			case <-stop:
				log.Println("Stop channel closed, exiting cron...")
				return nil
		}
	}
}
