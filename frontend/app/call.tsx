import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput, Image } from 'react-native';
import { Link } from 'expo-router';

export default function Call() {
  const [phoneNumber, setPhoneNumber] = useState('');

  const handleKeyPress = (digit: string) => {
    setPhoneNumber((prev) => (prev.length < 10 ? prev + digit : prev));
  };

  const handleDelete = () => {
    setPhoneNumber((prev) => prev.slice(0, -1));
  };

  const callHistory = [
    { id: '1', number: '9786897654', status: 'red' },
    { id: '2', number: '9786876547', status: 'red' },
    { id: '3', number: '9786878901', status: 'red' },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Calls</Text>

      <FlatList
        data={callHistory}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.callItem}>
            <Text style={styles.callNumber}>{item.number}</Text>
            <View
              style={[
                styles.statusIndicator,
                { backgroundColor: item.status === 'red' ? 'red' : 'green' },
              ]}
            />
          </View>
        )}
      />

      <Text style={styles.phoneNumber}>{phoneNumber}</Text>

      <View style={styles.keypad}>
        {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((digit) => (
          <TouchableOpacity
            key={digit}
            style={styles.key}
            onPress={() => handleKeyPress(digit)}
          >
            <Text style={styles.keyText}>{digit}</Text>
          </TouchableOpacity>
        ))}
        <TouchableOpacity style={styles.callButton}>
          <Link href="/recordscam">
          <Image
                source={require('@/assets/images/callingmain.webp')} // Adjust the path as necessary
                // style={styles.} // Add your desired styles
/>
          </Link>
        </TouchableOpacity>
        <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
          <Text style={styles.deleteText}>⌫</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f4f8',
    padding: 20,
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  callItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 15,
    padding: 10,
    borderRadius: 10,
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  callNumber: {
    fontSize: 18,
    color: '#000',
  },
  statusIndicator: {
    width: 15,
    height: 15,
    borderRadius: 7.5,
  },
  phoneNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 20,
    color: '#007BFF',
  },
  keypad: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    alignItems: 'center',
  },
  key: {
    width: '25%',
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
    margin: 5,
    borderWidth: 1,
    borderColor: '#007BFF',
    borderRadius: 10,
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  keyText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007BFF',
  },
  callButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#28a745',
    justifyContent: 'center',
    alignItems: 'center',
    margin: 10,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  callIcon: {
    width: 30,
    height: 30,
  },
  deleteButton: {
    width: 60,
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
    margin: 10,
  },
  deleteText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#dc3545',
  },
});