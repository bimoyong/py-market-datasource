bq_protoc_gen:
	protoc --bq-schema_out=./schema --bq-schema_opt=single-message datasource/news.proto --proto_path=./proto

bq_mk_dataset:
	bq mk 'datasource'

bq_mk_table:
	bq mk --table 'datasource.news' ./schema/datasource/news.schema

bq_upd_table:
	bq update --table 'datasource.news' ./schema/datasource/news.schema
