import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { Link } from 'expo-router';

export default function ThirdScreen() {
  return (
    <View style={styles.container}>
      {/* Illustration Section */}
      <View style={styles.illustrationContainer}>
        <Image
          source={require('../assets/images/thirdImage.png')} // Correct path to your image
          style={styles.image}
        />
      </View>

      {/* Title */}
      <Text style={styles.title}>
        <Text style={styles.highlight}>Record</Text> only unknown calls to verify them
      </Text>

      {/* Subtitle */}
      <Text style={styles.subtitle}>
        <Text style={styles.quote}>"Watch for urgency"</Text> — scammers create panic.
      </Text>

      {/* Start Button */}
      <Link href="/(tabs)/landing" style={styles.startButton}>
        <Text style={styles.startButtonText}>Start</Text>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9', // Light gray background for a clean look
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  illustrationContainer: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
  },
  image: {
    width: '70%', // Reduced width to fit better
    height: 200, // Keep the height consistent
    resizeMode: 'contain', // Maintain aspect ratio
    borderRadius: 10, // Add rounded corners for a modern look
    borderWidth: 2, // Add a border for emphasis
    borderColor: '#007BFF', // Blue border for a clean design
    shadowColor: '#000', // Add shadow for depth
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 5, // Shadow for Android
    marginBottom: 100,
  },
  title: {
    fontSize: 24, // Larger font size for the title
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#333', // Neutral dark color for better readability
    marginBottom: 10,
    lineHeight: 32, // Adds spacing between lines for better readability
  },
  highlight: {
    color: '#007BFF', // Blue color to highlight important words
    fontWeight: 'bold',
    fontSize: 26, // Slightly larger font size for emphasis
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    color: '#555', // Softer gray for a subtle look
    marginBottom: 30,
    paddingHorizontal: 20, // Adds padding for better alignment
    lineHeight: 24, // Improves readability
  },
  quote: {
    fontStyle: 'italic',
    color: '#FF6F61', // Highlighted color for the quote
    fontWeight: '600', // Slightly bold for emphasis
  },
  startButton: {
    backgroundColor: '#007BFF', // Blue button for a modern look
    paddingVertical: 15,
    paddingHorizontal: 100,
    borderRadius: 10,
    shadowColor: '#000', // Adds shadow for depth
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 5, // Shadow for Android
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: -100,
    marginTop: 40,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff', // White text for contrast
  },
});