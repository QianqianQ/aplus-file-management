FROM apluslms/service-base:python3-1.5
# create user
# RUN adduser --system --no-create-home --disabled-password --gecos "MOOC-Grader webapp server,,," --ingroup nogroup grader 
RUN pip3 install requests requests_toolbelt
ADD api.sh /bin/
ADD api.py /bin/
RUN chmod +x /bin/api.sh
ENTRYPOINT /bin/api.sh
# CMD ["python", "./api.py"]