import { View, Text, ScrollView, ActivityIndicator } from "react-native";

// Placeholder — applications endpoint will be implemented in sprint 2
export default function ApplicationsScreen() {
  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
    >
      <View className="items-center py-16">
        <Text className="text-4xl mb-3">⊕</Text>
        <Text className="text-text-primary font-semibold mb-1">No applications yet</Text>
        <Text className="text-muted text-sm text-center">
          When employers invite you to apply for a position, your applications will appear here.
        </Text>
      </View>
    </ScrollView>
  );
}
