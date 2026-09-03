import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('introduces the marketplace', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /borrow what you need\. share what you have\./i,
      }),
    ).toBeInTheDocument()
  })
})
