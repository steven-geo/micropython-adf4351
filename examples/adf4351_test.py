#Example code using the functions of the adf4351 library.
import adf4351
import time

# Set the Frequency
freq = 433  # MHz
adf4351.setfrequency(freq)

# Enable the Output
adf4351.enable()

print(f"Is the oscilator Locked: {adf4351.get_locked()}")

time.sleep(10)

# Disable the Output
adf4351.disable()

