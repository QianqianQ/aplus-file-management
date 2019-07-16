FROM apluslms/service-base:django-1.5

# create user
RUN adduser --system --no-create-home --disabled-password --gecos "MOOC-Grader webapp server,,," --ingroup nogroup grader 
RUN apt-get update && apt-get install curl
ADD api.sh /bin/
RUN chmod +x /bin/api.sh
ENTRYPOINT /bin/api.sh