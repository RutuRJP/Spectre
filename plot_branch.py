import matplotlib.pyplot as plt

bmr=[]

with open("dataset.txt") as f:
    for line in f:
        parts=line.split()
        bmr.append(float(parts[1]))

plt.hist(bmr, bins=20)
plt.xlabel("Branch Miss Rate (%)")
plt.title("Branch Predictor Behaviour")
plt.savefig("branch.png", dpi=300)
print("Graph saved as ipc_cache.png")
