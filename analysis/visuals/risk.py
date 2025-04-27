from plotnine import * 

def draw(risk_data, 
        x,
        y,
        title='Risk Metrics', 
        x_label='Risk Type', 
        y_label='Risk Score',
        color='steelblue',
        max_y=10):
    """
    Creates a horizontal bar chart visualization of risk scores.
    
    Parameters:
    -----------
    risk_data : pandas.DataFrame
        DataFrame containing risk metrics with 'risk_type' and 'risk_score' columns
    title : str, optional
        Plot title
    x_label : str, optional
        X-axis label
    y_label : str, optional
        Y-axis label
    color : str, optional
        Color of the bars
    max_y : int, optional
        Maximum value for y-axis scale
        
    Returns:
    --------
    ggplot object
        Ready-to-display visualization of risk scores
    """
    # Caption explaining risk calculation
    risk_caption = "Risk score (1-10) measures the volume and sentiment intensity\nof news coverage for each risk type."
    
    # Create visualization
    plot = (
        ggplot(risk_data.reset_index(), aes(x=f'reorder({x}, {y})', y=y)) +
        geom_bar(stat='identity', fill=color, color='black') +
        labs(
            title=title, 
            x=x_label, 
            y=y_label,
            caption=risk_caption
        ) +
        theme_bw(base_size=12) +
        theme(
            axis_text_x=element_text(rotation=45, hjust=1),
            plot_caption=element_text(size=9, hjust=0)
        ) +
        ylim(0, max_y) +
        coord_flip()
    )
    
    return plot