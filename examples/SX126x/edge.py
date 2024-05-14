import RPi.GPIO as GPIO
import time

IRQ_PIN = 16  # Use the same pin as in your main script

def edge_detected(channel):
    print("Edge detected on channel", channel)

def main():
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(IRQ_PIN, GPIO.RISING, callback=edge_detected)
        
        print("Waiting for edge detection. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except Exception as e:
        print("Error:", e)
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up")

if __name__ == "__main__":
    main()

