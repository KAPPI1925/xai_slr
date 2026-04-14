# #Install required pacakges
# install.packages("bibliometrix")
# install.packages("mergeDbsource")
# install.packages("xlsx")


#Librarries
library(xlsx)
library(devtools)
library(bibliometrix)


#Web of Science - .txt
web_data<-convert2df("wos.txt")

#Scopus - .bib
scopus_data<-convert2df("scopus.bib",dbsource="scopus",format="bibtex")

#Merge
M<-mergeDbSources(web_data,scopus_data,remove.duplicated=TRUE)


#Write to excel
write.xlsx(M,"M.xlsx")
biblioshiny()
