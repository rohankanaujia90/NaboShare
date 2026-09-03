import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  afterEach(() => {
    window.localStorage.clear()
    window.history.replaceState({}, '', '/')
  })

  it('introduces the marketplace', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /borrow what you need\. share what you have\./i,
      }),
    ).toBeInTheDocument()
  })

  it('redirects anonymous users away from protected routes', async () => {
    window.history.replaceState({}, '', '/app')
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: /log in/i }),
    ).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })
})
