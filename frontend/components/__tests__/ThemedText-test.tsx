import * as React from 'react';
import { render, screen } from '@testing-library/react-native';

import { ThemedText } from '../ThemedText';

// RNTL v14 render is async under React 19's concurrent root.
it(`renders correctly`, async () => {
  await render(<ThemedText>Snapshot test!</ThemedText>);

  expect(screen.getByText('Snapshot test!')).toBeOnTheScreen();
});
