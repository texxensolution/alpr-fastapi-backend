import sys
import time

def consume_memory():
    # List to store large amounts of data
    data = []
    
    try:
        # Continuously allocate memory by appending large objects to the list
        while True:
            data.append(' ' * 10**6)  # Allocate 1MB per iteration
            print(f"Memory consumed: {sys.getsizeof(data) / 1024 / 1024:.2f} MB")
    except MemoryError:
        print("Memory limit reached! System is out of memory.")

if __name__ == "__main__":
    consume_memory()
