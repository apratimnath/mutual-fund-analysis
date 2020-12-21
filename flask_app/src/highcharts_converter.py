import warnings
import numpy as np
warnings.filterwarnings('ignore')

'''
Contains all the functions required to create a Highcharts Series from the dataframe/list

Contains the following - 

1. determine_color = Color of the series based on the last set of values
2. create_box_plot = Creates a Box Plot chart
3. create_single_series_pie = Normal Pie Chart
4. create_multiple_series = Multiple Line Charts for comparision
'''

# Get the color based on the last two values


def determine_color(data, type_positive):
    value_list = list(map(lambda x: x[1], data.values.tolist()))

    if(type_positive):
        if(value_list[-1] > value_list[-2]):
            return 'green'
        elif(value_list[-1] < value_list[-2]):
            return 'red'
    else:
        if(value_list[-1] > value_list[-2]):
            return 'red'
        elif(value_list[-1] < value_list[-2]):
            return 'green'
    return 'orange'


def create_box_plot(data, x_axis_title, y_axis_title):
    series = {}

    # Creating the x-axis
    x_axis_categories = list(map(lambda x: x[0], data.values.tolist()))
    series['xAxis'] = {}
    series['xAxis']['categories'] = x_axis_categories
    series['xAxis']['title'] = {'text': x_axis_title}

    # Creating the y-axis
    series['yAxis'] = {}
    series['yAxis']['title'] = {'text': y_axis_title}
    plot_lines_array = []
    series['yAxis']['plotLines'] = plot_lines_array
    plot_lines_dict = {}
    plot_lines_dict['value'] = round(np.average(
        list(map(lambda x: x[3], data.values.tolist()))), 2)
    plot_lines_dict['color'] = 'red'
    plot_lines_dict['width'] = 1
    plot_lines_dict['label'] = {'text': 'Average Mean - ' + str(round(
        plot_lines_dict['value'], 2)), 'align': 'center', 'style': {'color': 'black'}}
    plot_lines_array.append(plot_lines_dict)

    # Creating the series
    # Drop the name column
    data = data.drop('month_year', axis=1)
    series_array = []
    series['series'] = series_array
    series_dict = {}
    series_dict['name'] = 'Observations'
    series_dict['data'] = data.values.tolist()
    series_array.append(series_dict)

    return series


def create_single_series_pie(data, series_name):
    series = {}

    # Creating the series
    series_array = []
    series['series'] = series_array
    series_dict = {}
    series_dict['type'] = 'pie'
    series_dict['name'] = series_name
    series_dict['data'] = data.values.tolist()
    series_array.append(series_dict)

    return series


def create_multiple_series(data1, data2, y_axis_title, series_1_name, series_2_name):
    series = {}

    # Creating the x-axis
    x_axis_categories = list(map(lambda x: x[0], data1.values.tolist()))
    series['xAxis'] = {}
    series['xAxis']['categories'] = x_axis_categories

    # Creating the y-axis
    series['yAxis'] = {}
    series['yAxis']['title'] = {'text': y_axis_title}

    # Creating the series
    series_array = []
    series['series'] = series_array
    # 1st Series
    series_dict1 = {}
    series_dict1['type'] = 'line'
    series_dict1['color'] = determine_color(data1, False)
    series_dict1['name'] = series_1_name
    series_dict1['data'] = list(map(lambda x: x[1], data1.values.tolist()))
    series_array.append(series_dict1)
    # 2nd Series
    series_dict2 = {}
    series_dict2['type'] = 'line'
    series_dict2['color'] = determine_color(data2, True)
    series_dict2['name'] = series_2_name
    series_dict2['data'] = list(map(lambda x: x[1], data2.values.tolist()))
    series_array.append(series_dict2)

    return series
