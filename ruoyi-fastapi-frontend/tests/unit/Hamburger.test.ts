import { describe, it, expect } from 'vitest';
import { render, fireEvent } from '@testing-library/vue';
import Hamburger from '@/components/ui/Hamburger/index.vue';

describe('Hamburger Component', () => {
  it('renders correctly', () => {
    const { container } = render(Hamburger);
    const svg = container.querySelector('.hamburger');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass('hamburger');
    expect(container.querySelector('.hamburger svg')).toBeInTheDocument();
  });

  it('applies active class when isActive is true', () => {
    const { container } = render(Hamburger, {
      props: {
        isActive: true,
      },
    });
    const svg = container.querySelector('.hamburger');
    expect(svg).toHaveClass('is-active');
  });

  it('does not apply active class when isActive is false', () => {
    const { container } = render(Hamburger, {
      props: {
        isActive: false,
      },
    });
    const svg = container.querySelector('.hamburger');
    expect(svg).not.toHaveClass('is-active');
  });

  it('emits toggleClick event when clicked', async () => {
    const { getByRole, emitted } = render(Hamburger);

    await fireEvent.click(getByRole('button', { name: '展开导航' }));

    expect(emitted('toggleClick')).toHaveLength(1);
  });

  it('has correct default props', () => {
    const { container } = render(Hamburger);
    const svg = container.querySelector('.hamburger');
    expect(svg).not.toHaveClass('is-active');
  });

  it('exposes the controlled navigation and its expanded state', async () => {
    const { getByRole, rerender } = render(Hamburger);
    const button = getByRole('button', { name: '展开导航' });
    expect(button).toHaveAttribute('type', 'button');
    expect(button).toHaveAttribute('aria-controls', 'app-sidebar');
    expect(button).toHaveAttribute('aria-expanded', 'false');

    await rerender({ isActive: true });
    expect(getByRole('button', { name: '收起导航' })).toHaveAttribute('aria-expanded', 'true');
  });

  it('keeps the collapsed brand decorative and retains the expansion action', async () => {
    const { getByRole, container, rerender } = render(Hamburger, {
      slots: { brand: '<img src="/brand.png" alt="" />' },
    });
    expect(getByRole('button', { name: '展开导航' })).toHaveClass('has-brand');
    expect(container.querySelector('.navigation-toggle-brand')).toHaveAttribute(
      'aria-hidden',
      'true'
    );

    await rerender({ isActive: true });
    expect(getByRole('button', { name: '收起导航' })).not.toHaveClass('has-brand');
    expect(container.querySelector('.navigation-toggle-brand')).not.toBeInTheDocument();
  });
});
