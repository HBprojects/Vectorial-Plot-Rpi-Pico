from machine import ADC
import time

# --- Configuration ---
ADC0_PIN = 26          # GPIO26 = ADC0
ADC1_PIN = 27          # GPIO27 = ADC1

VREF = 3.3
VMID = 1.1
GAIN = 2.6
ADC_MAX = 4095

adc0 = ADC(ADC0_PIN)
adc1 = ADC(ADC1_PIN)

def read_adc_voltage(adc, samples=8):
    acc = 0
    for _ in range(samples):
        acc += adc.read_u16() >> 4   # 12-bit value
    adc_raw = acc / samples

    v_adc = (adc_raw / ADC_MAX) * VREF
    v_diff = (v_adc - VMID) / GAIN

    return v_diff


# --- Main loop ---
while True:
    v0 = read_adc_voltage(adc0)
    v1 = read_adc_voltage(adc1)
    v3 = (v1 - v0)*-100
    v2 = (v1 - 0.31)*-100
    v1 = (v0 - 0.30)*-100
    

    # IMPORTANT: only numbers, comma-separated
    print("{:.5f},{:.5f},{:.5f}".format(v1, v2, v3))

    time.sleep(0.005)   # ~50 Hz (ideal for Thonny Plotter)
