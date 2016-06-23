import React from 'react';

function parseDate(string) {
    // date strings are formatted YYYY-MM-DD
    var year = parseInt(string.substring(0, 4));
    var month = parseInt(string.substring(5, 7)) - 1;
    var day = parseInt(string.substring(8, 10));
    var date = new Date(year, month, day);
    return date;
}

function collect(data, field) {
    // Collect just the data corresponding to a field
    return data.map(function(entry, index){
        return {
            date: parseDate(entry.fields['date']),
            data: entry.fields[field]
        }
    });
}

export const Value = React.createClass({
    render: function() {
        var data = collect(this.props.data, this.props.field);
        var valueData = data.map(function(entry, index){
            return entry.data;
        });
        var title = this.props.title;
        var total = valueData[0];
        var relative = total - valueData[valueData.length-1];
        var positive = relative > 0;
        return (
            <div className={this.props.field}>
                <div className="value__title">
                    {title}
                </div>
                <div className="value__total">
                    {total}
                </div>
                <div className="value__relative">
                    {relative}
                </div>
            </div>
        );
    }
});