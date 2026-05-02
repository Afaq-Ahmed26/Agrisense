import { reactive, computed } from 'vue';

export const officerStore = reactive({
    selectedFarmerId: localStorage.getItem('selectedFarmerId') || null,
    managedFarmers: []
});

export const isFarmerSelected = computed(() => !!officerStore.selectedFarmerId);

export function setSelectedFarmerId(farmerId) {
    officerStore.selectedFarmerId = farmerId;
    if (farmerId) {
        localStorage.setItem('selectedFarmerId', farmerId);
    } else {
        localStorage.removeItem('selectedFarmerId');
    }
}

export function setManagedFarmers(farmers) {
    officerStore.managedFarmers = farmers;
}

export function clearOfficerState() {
    officerStore.selectedFarmerId = null;
    officerStore.managedFarmers = [];
    localStorage.removeItem('selectedFarmerId');
}
