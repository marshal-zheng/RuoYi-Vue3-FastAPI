import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/vue';
import Hamburger from '@/components/Hamburger/index.vue';

describe('Hamburger Component', () => {
  it('renders correctly', () => {
    const { container } = render(Hamburger);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass('hamburger');
  });

  it('applies active class when isActive is true', () => {
    const { container } = render(Hamburger, {
      props: {
        isActive: true,
      },
    });
    const svg = container.querySelector('svg');
    expect(svg).toHaveClass('is-active');
  });

  it('does not apply active class when isActive is false', () => {
    const { container } = render(Hamburger, {
      props: {
        isActive: false,
      },
    });
    const svg = container.querySelector('svg');
    expect(svg).not.toHaveClass('is-active');
  });

  it('emits toggleClick event when clicked', async () => {
    const mockToggleClick = vi.fn();
    const { container } = render(Hamburger, {
      props: {
        onToggleClick: mockToggleClick,
      },
    });

    const clickableDiv = container.querySelector('div');
    await fireEvent.click(clickableDiv!);

    expect(mockToggleClick).toHaveBeenCalledTimes(1);
  });

  it('has correct default props', () => {
    const { container } = render(Hamburger);
    const svg = container.querySelector('svg');
    expect(svg).not.toHaveClass('is-active');
  });

  it('has correct styling', () => {
    const { container } = render(Hamburger);
    const clickableDiv = container.querySelector('div');
    expect(clickableDiv).toHaveStyle('padding: 0 15px');
  });
});
