from plotnine import *
import pandas as pd

def draw(df, column, title='Political Risk Over Time', x_label='Date', y_label='Risk Score'):
    """
    Create a plot of risk over time using plotnine.
    Args:
        df (DataFrame): DataFrame containing the data to plot
        column (str): Column name to use for color grouping
        title (str): Plot title
        x_label (str): X-axis label
        y_label (str): Y-axis label
    Returns:
        ggplot object
    """
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create pivot table and melt for plotting
    pivot = pd.pivot_table(
        df,
        values='Score',
        index=column,  # Use the specified column parameter for grouping
        columns='Date',
        fill_value=3
    )
    
    result = pivot.reset_index().melt(
        id_vars=column,  # Use the specified column parameter for id_vars
        var_name='Date',
        value_name='Score'
    )
    
    result['Date'] = pd.to_datetime(result['Date'])
    total_scores = result.groupby(column)['Score'].sum().sort_values(ascending=False)
    result[column] = pd.Categorical(result[column], categories=total_scores.index, ordered=True)
    

    # Create and return plot
    return (
        ggplot(result, aes(x='Date', y='Score', fill=column, color=column)) +
        geom_area(alpha=.9, position='identity', size = .5) +
        labs(
            title=title,
            x=x_label,
            y=y_label
        ) +
        theme_bw() +
        scale_x_datetime(
            date_breaks='1 month',
            date_labels='%b %Y'
        ) +


        theme(
            legend_title=element_blank(),
            axis_text_x=element_text(angle=45, hjust=1),
            figure_size=(7.5, 3.5),
            panel_grid_minor=element_blank(),
            legend_position='top',
            dpi=300
        ) +
        # # Use brewer scales with manual color selection to ensure darkest reds
        # scale_color_brewer(type='seq', palette='Reds', direction=-1) +
        # scale_fill_brewer(type='seq', palette='Reds', direction=-1)
        scale_color_brewer(type='div', palette='RdYlBu') +
        scale_fill_brewer(type='div', palette='RdYlBu')
    )
