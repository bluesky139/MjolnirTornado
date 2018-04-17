from tornado.options import options

def get_service_host(service):
	return '%s-%s%s%s.%s' % (
		options.region, 
		service, 
		'-' if options.host_extra else '', 
		options.host_extra, 
		options.domain
	)

def get_service_host_internal(service):
	return '%s-%s-internal%s%s.%s' % (
		options.region, 
		service, 
		'-' if options.host_extra else '', 
		options.host_extra, 
		options.domain
	)