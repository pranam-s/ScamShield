import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, Alert, StyleSheet, Image } from 'react-native';
import { File } from 'expo-file-system';
import * as ExpoCrypto from 'expo-crypto';
import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorder,
} from 'expo-audio';

import { DETECT_SCAM_ENDPOINT, CHUNK_INTERVAL_MS } from '../constants/Api';

/**
 * Encode an ArrayBuffer as base64 without native helpers: RN's Hermes engine
 * provides `btoa` (since 0.74) but only accepts binary strings, so the bytes
 * are folded into a string in 32 KB slices to stay well inside the engine's
 * argument-count limits.
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const sliceSize = 0x8000;
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += sliceSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + sliceSize));
  }
  return btoa(binary);
}

const RecordScam: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [callId, setCallId] = useState<string | null>(null);
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recordingInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    void requestPermissions();
    return () => {
      if (recordingInterval.current) {
        clearInterval(recordingInterval.current);
      }
    };
  }, []);

  const requestPermissions = async () => {
    const { status } = await AudioModule.requestRecordingPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Please grant microphone permission to use this feature.');
      console.error('Permission denied.');
    } else {
      console.log('Microphone permission granted.');
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
      await setAudioModeAsync({
        playsInSilentMode: true,
        allowsRecording: true,
      });
      const newCallId = await generateCallId();
      setCallId(newCallId);
      setIsRecording(true);
      await startNewRecording();

      recordingInterval.current = setInterval(() => {
        void processCurrentChunk(newCallId).then(() => startNewRecording());
      }, CHUNK_INTERVAL_MS);
    } catch (error) {
      console.error('Error starting recording:', error);
      Alert.alert('Error', `Failed to start recording: ${error}`);
      setIsRecording(false);
    }
  };

  const startNewRecording = async () => {
    try {
      await recorder.prepareToRecordAsync();
      recorder.record();
      console.log('Recording started successfully');
    } catch (error) {
      console.error('Error preparing or starting the recording:', error);
      throw new Error('Failed to prepare or start recording');
    }
  };

  const processCurrentChunk = async (chunkCallId: string) => {
    try {
      await recorder.stop();
      const uri = recorder.uri;
      if (uri) {
        const chunkFile = new File(uri);
        const audioBytes = arrayBufferToBase64(await chunkFile.arrayBuffer());
        await sendAudioToUrl(chunkCallId, audioBytes);
      }
    } catch (error) {
      console.error('Error processing audio chunk:', error);
    }
  };

  const sendAudioToUrl = async (chunkCallId: string, base64Audio: string) => {
    try {
      const response = await fetch(DETECT_SCAM_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          call_id: chunkCallId,
          base64: base64Audio,
        }),
      });

      if (response.ok) {
        const responseData = await response.json();

        // Check if the status is "scam"
        if (responseData.status === 'Scam') {
          Alert.alert(
            'Warning: Scam Detected',
            'This call is identified as a scam. We recommend cutting the call immediately.',
            [
              {
                text: 'Cut Call',
                onPress: () => {
                  void stopRecording(); // Optionally stop recording if the user chooses to cut the call
                },
                style: 'destructive',
              },
              {
                text: 'Ignore',
                onPress: () => {
                  // User chose to stay on the call; recording continues.
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
    try {
      await recorder.stop();
    } catch {
      // Stopping an already-stopped recorder throws on some platforms; safe to ignore.
    }
    setCallId(null);
  };

  return (
    <View style={styles.container}>
      <Image
        source={require('../assets/images/recording.jpg')}
        style={styles.headerImage}
      />
      <Text style={styles.title}>
        {isRecording ? `Recording... (Call ID: ${callId})` : 'Press to Start Recording'}
      </Text>
      <TouchableOpacity
        onPress={isRecording ? stopRecording : startRecording}
        style={[styles.button, { backgroundColor: isRecording ? 'red' : 'green' }]}
        accessibilityRole="button"
        accessibilityLabel={isRecording ? 'Stop recording' : 'Start recording'}
        accessibilityState={{ busy: isRecording }}
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
