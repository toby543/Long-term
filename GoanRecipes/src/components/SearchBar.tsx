import React from 'react';
import { StyleSheet, TextInput, View } from 'react-native';
import { colors } from '../theme';

interface Props {
  value: string;
  onChange: (text: string) => void;
  placeholder?: string;
}

export default function SearchBar({ value, onChange, placeholder }: Props) {
  return (
    <View style={styles.wrapper}>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={placeholder ?? 'Search recipes, ingredients...'}
        placeholderTextColor={colors.subtext}
        style={styles.input}
        autoCorrect={false}
        returnKeyType="search"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 14,
    marginBottom: 12,
  },
  input: {
    paddingVertical: 10,
    fontSize: 15,
    color: colors.text,
  },
});
