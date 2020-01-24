objdump -t odu.elf > odu.dump.txt
objsort odu.dump.txt
gawk -f odu.ram.awk odu.dump.out
