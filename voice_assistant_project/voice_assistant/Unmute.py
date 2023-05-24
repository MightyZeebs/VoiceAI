from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

def unmute_audio():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        # Unmute the volume
        volume.SetMute(False, None)

# Call the unmute_audio() function to unmute the audio
unmute_audio()
