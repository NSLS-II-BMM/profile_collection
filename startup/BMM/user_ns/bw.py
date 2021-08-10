#from bluesky_widgets.utils.streaming import stream_documents_into_runs
#from bluesky_widgets.models.plot_builders import Lines
#from bluesky_widgets.qt.figures import QtFigure

#model = Lines("motor", ["det"], max_runs=3)
#view = QtFigure(model.figure)
#view.show()

#RE.subscribe(stream_documents_into_runs(model.add_run))



# fig=Figure([ax1,ax2], title='Hi there!')                                                          
# model = Lines("xafs_y", ["I0/It"], axes=ax1, max_runs=3)                                          
# model2 = Lines("xafs_y", ["I0"], axes=ax2, max_runs=3)                                            
# view = QtFigure(fig)                                                                              
# view.show()                                                                                       
# RE.subscribe(stream_documents_into_runs(model.add_run))                                           
# RE.subscribe(stream_documents_into_runs(model2.add_run))

# "It's just matplotlib, google it."
# BMM D.111 [46] ▶ view.figure
# Out[46]: <Figure size 682x610 with 2 Axes>
