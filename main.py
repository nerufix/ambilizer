from pyaudio_stream import *
import hyperion_client as hy

import numpy as np
import time
import msvcrt

HOSTNAME = "localhost"
PORT = 19444  # Hyperion JSON port
REFRESH_RATE = 60


# assign a peak from frequency chunks to every LED
def chunker(tab, count):
    arr = []
    avg = len(tab) // count
    repeat = count // (avg * 2)
    width = 1
    for i in range(count):
        mid = (avg - 1) * repeat < i < count - avg * repeat
        if i > 0 and i % repeat == 0 and not mid:
            width += 1
        arr.append(max(tab[0:width]))
        tab = tab[width:]
    return arr


stream = open_stream()

h = hy.hyperion_client(HOSTNAME, PORT)
h.open_connection()

led_count = len(h.serverinfo()['info']['leds'])
bassrange = 17000
trebrange = 3000
basspeaks = []
trebpeaks = []

lastgoodtreb = [0 for i in range(led_count)]
lastgoodbass = 0

print("Connected to server. Sending data...")

freq = np.fft.fftfreq(DEFAULT_FRAMES, 1.0 / rate)
freq = freq[:int(len(freq) / 2)]
assert freq[-1] > 500, "ERROR: increase chunk size"
slice = []
for i in range(len(freq)):
    if freq[i] < 500 <= freq[i + 1]:
        slice.append(i)
    elif freq[i] < 1000 <= freq[i + 1]:
        slice.append(i)
    elif freq[i] < 5000 <= freq[i + 1]:
        slice.append(i)
        break

while not msvcrt.kbhit():
    data = np.frombuffer(stream.read(DEFAULT_FRAMES), dtype=np.int16)
    fft = abs(np.fft.fft(data).real)
    fft = fft[:int(len(fft) / 2)]
    peakindex = int(np.where(fft[slice[1]:slice[2]] == max(fft[slice[1]:slice[2]]))[0][0]) + slice[1]
    basstab = fft[1:slice[0]]
    trebtab = fft[slice[1]:slice[2]]

    bass = max(basstab)
    bass = bass // bassrange
    tab_to_send = []
    bass = bass if bass < 255 else 255
    if abs(bass - lastgoodbass) < 11 and bass < 220:
        bass = lastgoodbass
    lastgoodbass = bass

    peaks = chunker(trebtab, led_count)

    for i in range(len(peaks)):
        peaks[i] = peaks[i] // trebrange if peaks[i] // trebrange < 255 else 255
        if abs(peaks[i] - lastgoodtreb[i]) < 11 and peaks[i] < 220:
            peaks[i] = lastgoodtreb[i]
        lastgoodtreb[i] = peaks[i]

    bassratio = min(bass / max(peaks) if max(peaks) > 0 else 0.5, 1)
    trebratio = 1 - bassratio
    for i in range(led_count):
        # different visualization
        """
        treble = peaks[len(peaks) - i - 1]*0.7+bass*0.3
        tab_to_send.extend(
            [int(treble * bassratio) if int(treble * bassratio) > 40 else 40,
             0,
             int(treble * trebratio) if int(treble * trebratio) > 40 else 40])
         """

        treble = peaks[len(peaks) - i - 1]
        tab_to_send.extend(
            [int(treble * bassratio) if int(treble * bassratio) > 40 else bass if bass > 40 else 40,
             0,
             int(treble * trebratio) if int(treble * trebratio) > 40 else 40])

    if bass > 0:
        basspeaks.append(bass)
        trebpeaks.append(sum(peaks) / len(peaks))

    sensitivity = 45
    if len(basspeaks) == 40:
        avg = sum(basspeaks) // len(basspeaks)
        if avg < sensitivity - 15 and bassrange > 2000:
            bassrange *= max(avg / (sensitivity - 5), 0.75)
        elif avg > sensitivity + 5:
            bassrange *= min(avg / (sensitivity - 5), 2)
        basspeaks = []

    if len(trebpeaks) == 40:
        avg = sum(trebpeaks) // len(trebpeaks)
        if (avg < sensitivity and trebrange > 2000) or avg > sensitivity + 20:
            trebrange *= avg / (sensitivity + 10)
        trebpeaks = []
    h.send_led_data(tab_to_send)
    time.sleep(1 / REFRESH_RATE)

print("Exiting...")
time.sleep(1)
h.clear('100')
time.sleep(1)
h.close_connection()
stream.stop_stream()
stream.close()
p.terminate()
