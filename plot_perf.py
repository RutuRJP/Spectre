import matplotlib.pyplot as plt

ipc=[]
cmr=[]

with open("dataset.txt") as f:
    for line in f:
        parts=line.split()
        ipc.append(float(parts[0]))
        cmr.append(float(parts[2]))

plt.scatter(ipc, cmr)
plt.xlabel("IPC")
plt.ylabel("Cache Miss Rate (%)")
plt.title("IPC vs Cache Miss Behaviour")
plt.savefig("ipc_cache.png", dpi=300)
print("Graph saved as ipc_cache.png")
