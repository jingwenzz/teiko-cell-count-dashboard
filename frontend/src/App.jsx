import { useEffect, useMemo, useState } from 'react'
import './App.css'

function useJson(url) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`${url}: ${res.status}`)
        return res.json()
      })
      .then(setData)
      .catch((err) => setError(err.message))
  }, [url])

  return { data, error }
}

function FrequencySummary() {
  const { data, error } = useJson('/api/summary')
  const [sampleId, setSampleId] = useState('')

  const samples = useMemo(() => {
    if (!data) return []
    return [...new Set(data.map((row) => row.sample))].sort()
  }, [data])

  const activeSample = sampleId || samples[0] || ''
  const rows = data ? data.filter((row) => row.sample === activeSample) : []

  return (
    <section className="card">
      <h2>Part 2 — Population frequency per sample</h2>
      {error && <p className="error">Failed to load: {error}</p>}
      {!data && !error && <p>Loading…</p>}
      {data && (
        <>
          <label className="field">
            Sample:
            <select value={activeSample} onChange={(e) => setSampleId(e.target.value)}>
              {samples.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <table>
            <thead>
              <tr>
                <th>Population</th>
                <th>Count</th>
                <th>Percentage</th>
                <th>Total count</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.population}>
                  <td>{row.population}</td>
                  <td>{row.count.toLocaleString()}</td>
                  <td>{row.percentage.toFixed(2)}%</td>
                  <td>{row.total_count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="hint">{data.length / 5} samples total — pick any one above.</p>
        </>
      )}
    </section>
  )
}

function ResponderStats() {
  const { data, error } = useJson('/api/significance')

  return (
    <section className="card">
      <h2>Part 3 — Responders vs non-responders (melanoma, miraclib, PBMC)</h2>
      {error && <p className="error">Failed to load: {error}</p>}
      {!data && !error && <p>Loading…</p>}
      {data && (
        <>
          <img
            src="/api/boxplot.png"
            alt="Boxplot of relative frequency per population, responders vs non-responders"
            className="boxplot"
          />
          <table>
            <thead>
              <tr>
                <th>Population</th>
                <th>Median (responders)</th>
                <th>Median (non-responders)</th>
                <th>p-value</th>
                <th>p-value (FDR)</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.population}>
                  <td>{row.population}</td>
                  <td>{row.median_responders.toFixed(2)}%</td>
                  <td>{row.median_non_responders.toFixed(2)}%</td>
                  <td>{row.p_value.toFixed(4)}</td>
                  <td className={row['significant_fdr<0.05'] ? 'significant' : ''}>
                    {row.p_value_adjusted.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="hint">
            Mann-Whitney U test per population, with Benjamini-Hochberg FDR
            correction across the 5 populations tested.
          </p>
        </>
      )}
    </section>
  )
}

function BaselineSubset() {
  const { data: subset, error: subsetError } = useJson('/api/baseline-subset')
  const { data: finalAnswer, error: finalError } = useJson('/api/final-answer')

  return (
    <section className="card">
      <h2>Part 4 — Melanoma / PBMC / miraclib baseline (time=0)</h2>
      {(subsetError || finalError) && (
        <p className="error">Failed to load: {subsetError || finalError}</p>
      )}
      {subset && (
        <div className="breakdown">
          <div>
            <h3>Samples per project</h3>
            <ul>
              {Object.entries(subset.samples_per_project).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Subjects by response</h3>
            <ul>
              {Object.entries(subset.subjects_by_response).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Subjects by sex</h3>
            <ul>
              {Object.entries(subset.subjects_by_sex).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {finalAnswer && (
        <p className="final-answer">
          Average B cell count — melanoma males, all sample/treatment types,
          responders, time=0:{' '}
          <strong>{finalAnswer.avg_b_cells_melanoma_male_responders_t0.toFixed(2)}</strong>
        </p>
      )}
    </section>
  )
}

export default function App() {
  return (
    <main className="dashboard">
      <h1>Teiko Cell Count Dashboard</h1>
      <p className="subtitle">
        Immune cell population analysis for Bob Loblaw's miraclib trial
      </p>
      <FrequencySummary />
      <ResponderStats />
      <BaselineSubset />
    </main>
  )
}
