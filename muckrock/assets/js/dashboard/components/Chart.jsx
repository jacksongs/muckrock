import React from 'react';
import rd3 from 'rd3';

function parseDate(string) {
    // date strings are formatted YYYY-MM-DD
    var year = parseInt(string.substring(0, 4));
    var month = parseInt(string.substring(5, 7)) - 1;
    var day = parseInt(string.substring(8, 10));
    var date = new Date(year, month, day);
    return date;
}

export const Chart = React.createClass({
    collect: function(field) {
        // Collect just the data corresponding to a field
        return this.props.data.map(function(entry, index){
            return {
                date: parseDate(entry.fields['date']),
                data: entry.fields[field]
            }
        });
    },
    render: function() {
        const LineChart = rd3.LineChart;
        var data = this.collect(this.props.field);
        var chartData = [];
        if (data.length) {
            chartData = [
                {
                    name: 'series1',
                    values: data.map(function(entry, index){
                        return {
                            x: entry.date,
                            y: entry.data,
                        }
                    }),
                }
            ];
        }
        return (
            <div className={this.props.field}>
                <LineChart
                    legend={false}
                    data={chartData}
                    width={600}
                    height={400}
                    title={this.props.title}
                    xAxisLabel='Date'
                />
            </div>
        );
    }
});
