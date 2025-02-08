import React from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';

const History: React.FC = () => {
  // Sample call logs data
  const callLogs = [
    { id: '1', number: '9087678989', date: '06/02/25', time: '14:13' },
    { id: '2', number: '9087678989', date: '07/02/25', time: '17:56' },
    { id: '3', number: '9087678989', date: '07/02/25', time: '18:23' },
    { id: '4', number: '9087678989', date: '07/02/25', time: '22:34' },
    { id: '5', number: '9087678989', date: '07/02/25', time: '23:48' },
  ];

  // Render each call log item
  const renderCallLog = ({ item }: { item: typeof callLogs[0] }) => (
    <View style={styles.card}>
      <Text style={styles.number}>{item.number}</Text>
      <Text style={styles.dateTime}>
        {item.date} {item.time}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Call Logs</Text>
      <FlatList
        data={callLogs}
        renderItem={renderCallLog}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    paddingHorizontal: 20,
    paddingTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  listContainer: {
    paddingBottom: 20,
  },
  card: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3, // For Android shadow
  },
  number: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  dateTime: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
});

export default History;