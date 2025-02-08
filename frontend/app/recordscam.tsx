import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TouchableOpacity, Alert, StyleSheet, Image } from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import * as ExpoCrypto from 'expo-crypto';

const RecordScam: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [callId, setCallId] = useState<string | null>(null);
  const recording = useRef<Audio.Recording | null>(null);
  const recordingInterval = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    requestPermissions();
    return () => {
      if (recordingInterval.current) {
        clearInterval(recordingInterval.current);
      }
      if (recording.current) {
        recording.current.stopAndUnloadAsync().catch(() => {});
      }
    };
  }, []);

  const requestPermissions = async () => {
    const { status } = await Audio.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Please grant microphone permission to use this feature.');
      console.error("Permission denied.");
    } else {
      console.log("Microphone permission granted.");
    }
  };

  const generateCallId = async () => {
    const randomBytes = await ExpoCrypto.getRandomBytesAsync(16);
    return Array.from(randomBytes)
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('');
  };

  const startRecording = async () => {
    try {
      const newCallId = await generateCallId();
      setCallId(newCallId);
      setIsRecording(true);
      await startNewRecording();

      recordingInterval.current = setInterval(async () => {
        await processCurrentChunk(newCallId);
        await startNewRecording();
      }, 10000);
    } catch (error) {
      console.error('Error starting recording:', error);
      Alert.alert('Error', `Failed to start recording: ${error}`);
      setIsRecording(false);
    }
  };

  const startNewRecording = async () => {
    if (recording.current) {
      await recording.current.stopAndUnloadAsync();
      recording.current = null;
    }

    try {
      recording.current = new Audio.Recording();
      await recording.current.prepareToRecordAsync({
        android: {
          extension: '.3gp',
          outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_THREE_GPP,
          audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_AAC,
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_HIGH,
          sampleRate: 44100,
          numberOfChannels: 2,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/m4a',
          bitsPerSecond: 128000,
        },
      });

      await recording.current.startAsync();
      console.log('Recording started successfully');
    } catch (error) {
      console.error('Error preparing or starting the recording:', error);
      throw new Error('Failed to prepare or start recording');
    }
  };

  const processCurrentChunk = async (callId: string) => {
    if (recording.current) {
      try {
        await recording.current.stopAndUnloadAsync();
        const uri = recording.current.getURI();
        if (uri) {
          const audioBytes = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
          console.log(`Audio Chunk for Call ID ${callId}:`, audioBytes);
          await sendAudioToUrl(callId, audioBytes); 
        }
      } catch (error) {
        console.error('Error processing audio chunk:', error);
      } finally {
        recording.current = null;
      }
    }
  };
  
  const sendAudioToUrl = async (callId: string, base64Audio: string) => {
    const url = 'https://precise-divine-lab.ngrok-free.app/detect-scam/';
  
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          call_id: callId, 
          base64: base64Audio
        }),
      });
  
      if (response.ok) {
        const responseData = await response.json();
        console.log("Response received successfully:", responseData);
        
        // Check if the status is "scam"
        if (responseData.status === 'Scam') {
          Alert.alert(
            'Warning: Scam Detected',
            'This call is identified as a scam. We recommend cutting the call immediately.',
            [
              {
                text: 'Cut Call',
                onPress: () => {
                  console.log('Call cut by user');
                  stopRecording(); // Optionally stop recording if the user chooses to cut the call
                },
                style: 'destructive',
              },
              {
                text: 'Ignore',
                onPress: () => {
                  console.log('User ignored the suggestion');
                },
              },
            ],
            { cancelable: false }
          );
        }
      } else {
        console.error('Failed to send audio data:', response.status);
      }
    } catch (error) {
      console.error('Error sending audio data to URL:', error);
    }
  };
  
  const stopRecording = async () => {
    setIsRecording(false);
    if (recordingInterval.current) {
      clearInterval(recordingInterval.current);
      recordingInterval.current = null;
    }
    if (recording.current) {
      await recording.current.stopAndUnloadAsync();
      recording.current = null;
    }
    setCallId(null);
  };

  return (
    <View style={styles.container}>
      <Image
        source={require('../assets/images/recording.jpg')} // Ensure the image path is correct
        style={styles.headerImage}
      />
      <Text style={styles.title}>
        {isRecording ? `Recording... (Call ID: ${callId})` : 'Press to Start Recording'}
      </Text>
      <TouchableOpacity
        onPress={isRecording ? stopRecording : startRecording}
        style={[styles.button, { backgroundColor: isRecording ? 'red' : 'green' }]}
      >
        <Text style={styles.buttonText}>{isRecording ? 'Stop' : 'Start'}</Text>
      </TouchableOpacity>
      <Text style={styles.instructionText}>
        {isRecording ? 'Tap the button to stop recording.' : 'Tap the button to start recording your calls.'}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
    padding: 20,
  },
  headerImage: {
    width: '100%',
    height: 200,
    marginBottom: 20,
    borderRadius: 10,
    overflow: 'hidden',
  },
  title: {
    fontSize: 24,
    marginBottom: 20,
    textAlign: 'center',
    color: '#333',
    fontWeight: 'bold',
  },
  button: {
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    width: '80%',
    marginVertical: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  instructionText: {
    fontSize: 16,
    textAlign: 'center',
    color: '#555',
    marginTop: 10,
  },
});

export default RecordScam;