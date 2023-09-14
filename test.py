from pydub import AudioSegment

sound = AudioSegment.from_mp3("./user_audio.mp3")
sound.export('./user_audio.ogg', format='ogg')