CC = gcc
CCFLAGS = -Wall --pedantic -O2 -w -g

controller: obj/controller.o obj/device_functions.o obj/time_functions.o obj/common_functions.o obj/invariant_functions.o obj/single_functions.o obj/stimulation_functions.o
	g++ $(CCFLAGS) -o controller obj/controller.o obj/device_functions.o obj/time_functions.o obj/common_functions.o obj/invariant_functions.o obj/single_functions.o obj/stimulation_functions.o -lm -lserial -lcomedi -lpthread

obj/controller.o: src/controller.cpp obj/device_functions.o obj/time_functions.o obj/common_functions.o
	g++ $(CCFLAGS) -Iserial -c src/controller.cpp -o obj/controller.o -lm

obj/common_functions.o: src/common_functions.cpp includes/common_functions.h obj/invariant_functions.o obj/single_functions.o obj/stimulation_functions.o
	g++ $(CCFLAGS) -Iserial -c src/common_functions.cpp -o obj/common_functions.o -lm

obj/invariant_functions.o: src/invariant_functions.cpp includes/invariant_functions.h includes/types.h
	g++ $(CCFLAGS) -Iserial -c src/invariant_functions.cpp -o obj/invariant_functions.o -lm

obj/single_functions.o: src/single_functions.cpp includes/single_functions.h includes/types.h
	g++ $(CCFLAGS) -Iserial -c src/single_functions.cpp -o obj/single_functions.o -lm

obj/stimulation_functions.o: src/stimulation_functions.cpp includes/stimulation_functions.h includes/types.h
	g++ $(CCFLAGS) -Iserial -c src/stimulation_functions.cpp -o obj/stimulation_functions.o -lm

obj/time_functions.o: src/time_functions.c includes/time_functions.h
	$(CC) $(CCFLAGS) -c src/time_functions.c -o obj/time_functions.o -lm

obj/device_functions.o: src/comedi_functions.c includes/device_functions.h
	$(CC) $(CCFLAGS) -c src/comedi_functions.c -o obj/device_functions.o -lm -lcomedi

clean:
	rm -f controller obj/*.o
