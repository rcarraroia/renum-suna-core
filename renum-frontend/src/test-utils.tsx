import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { useRouter } from 'next/router';

// Create a custom render function that includes providers if needed
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { routerMock?: Partial<ReturnType<typeof useRouter>> }
) => {
  const { routerMock = {}, ...renderOptions } = options || {};

  // Setup router mock with custom values if provided
  if (Object.keys(routerMock).length > 0) {
    useRouter.mockImplementation(() => ({
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      reload: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
      isReady: true,
      ...routerMock,
    }));
  }

  // Add providers here if needed
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return (
      <>{children}</>
    );
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Re-export everything from testing-library
export * from '@testing-library/react';

// Override render method
export { customRender as render };