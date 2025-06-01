#Example code using the functions of the adf4351 library.
import adf435x
import time

# Set the Frequency
freq = 433  # MHz
adf435x.setfrequency(freq)

# Enable the Output
adf435x.enable()

print(f"Is the oscilator Locked: {adf435x.get_locked()}")

sleep(10)

# Disable the Output
adf435x.disable()

