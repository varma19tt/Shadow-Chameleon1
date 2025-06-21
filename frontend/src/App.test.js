import { render, screen } from '@testing-library/react';
import App from './App';

test('renders main title', () => {
  render(<App />);
  const titleElement = screen.getByText(/SHADOW CHAMELEON/i);
  expect(titleElement).toBeInTheDocument();
});

test('analyze button exists', () => {
  render(<App />);
  const buttonElement = screen.getByText(/Analyze Target/i);
  expect(buttonElement).toBeInTheDocument();
});
