import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { useRouter } from 'next/router';

// Mock useRouter
jest.mock('next/router', () => ({
  useRouter: jest.fn()
}));

const mockedUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

// Create a custom render function that includes providers if needed
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { routerMock?: Partial<ReturnType<typeof useRouter>> }
) => {
  const { routerMock = {}, ...renderOptions } = options || {};

  // Setup router mock with custom values if provided
  if (Object.keys(routerMock).length > 0) {
    mockedUseRouter.mockImplementation(() => ({
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      reload: jest.fn(),
      beforePopState: jest.fn(),
      pathname: '/',
      route: '/',
      query: {},
      asPath: '/',
      basePath: '',
      locale: undefined,
      locales: undefined,
      defaultLocale: undefined,
      domainLocales: undefined,
      isLocaleDomain: false,
      isPreview: false,
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