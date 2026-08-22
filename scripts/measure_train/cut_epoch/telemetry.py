def project(consumer,cut,census_rows):
    return tuple({"activity":"measure_cut_epoch","consumer_repo":consumer.repo,"consumer_sha":consumer.sha,
                  "cut_id":cut.cut_id,"cut_generation":cut.generation,"producer_repo":repo,"state":state}
                 for repo,state in census_rows)
