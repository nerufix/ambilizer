import pyaudiowpatch as pyaudio

DEFAULT_FRAMES = 1024

p = pyaudio.PyAudio()

print("Available devices:\n")
for i in range(0, p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(str(info["index"]) + ": \t %s \n \t %s \n" % (
    info["name"], p.get_host_api_info_by_index(info["hostApi"])["name"]))

device_id = int(input("Choose device: "))
device_info = p.get_device_info_by_index(device_id)
rate = int(device_info["defaultSampleRate"])

if device_info["maxOutputChannels"] < device_info["maxInputChannels"]:
    channel_count = device_info["maxInputChannels"]
else:
    channel_count = device_info["maxOutputChannels"]


def open_stream():
    return p.open(format=pyaudio.paInt16,
                  channels=channel_count,
                  rate=rate,
                  input=True,
                  frames_per_buffer=DEFAULT_FRAMES,
                  input_device_index=device_info["index"])
