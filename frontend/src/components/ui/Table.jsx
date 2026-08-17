import React from 'react'
import Card from '@/components/ui/Card'

function Table({ headers = [], rows = [] }) {
  return (
    <div className="ui-table-wrapper">
      <Card>
        <div className="overflow-x-auto">
          <table className="ui-table">
            <thead>
              <tr>
                {headers.map((h, idx) => (
                  <th key={idx}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className="row-hover">
                  {row.map((col, cIdx) => (
                    <td key={cIdx}>{col}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

export default Table
