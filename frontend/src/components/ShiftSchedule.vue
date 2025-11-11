<template>
  <div class="shift-schedule-container">
    <el-alert title="Manual Shift Scheduler" type="info" description="Select a date to view, add, modify, or delete shifts." show-icon :closable="true" style="margin-bottom: 20px;"/>
    
    <el-calendar v-model="selectedDate">
      <template #date-cell="{ data }">
        <div 
          class="calendar-day" 
          @click="openDetailDialog(data.day)"
          :class="{'is-selected': data.day === today}"
        >
          <p class="day-number">{{ data.day.split('-').slice(2).join('') }}</p>
          <div v-if="shiftsByDate[data.day]" class="shift-count-badge">
            <el-tag size="small" type="success" effect="dark">
              {{ shiftsByDate[data.day].length }} Shift(s)
            </el-tag>
          </div>
        </div>
      </template>
    </el-calendar>

    <el-dialog v-model="detailDialogVisible" :title="`${selectedDay} Shift Details`" width="700px">
      <h3>Current Shifts</h3>
      <el-table :data="shiftsForSelectedDay" style="width: 100%;" border max-height="300">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="staff_name" label="Staff Name" width="180" />
        <el-table-column prop="shift_type" label="Shift Type" width="120" />
        <el-table-column label="Actions">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openShiftForm(row)">Edit</el-button>
            <el-button size="small" type="danger" @click="deleteShift(row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-divider />

      <h3>{{ isEditing ? 'Edit Shift Record' : 'Add Shift Record' }}</h3>
      <el-form :model="shiftForm" label-width="80px" v-loading="shiftLoading" class="shift-form-area">
        <el-form-item label="Staff">
          <el-select v-model="shiftForm.staff_id" placeholder="Select Staff">
            <el-option v-for="staff in staffList" :key="staff.id" :label="staff.name" :value="staff.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Shift Type">
          <el-select v-model="shiftForm.shift_type" placeholder="Select Shift Type">
            <el-option label="Morning" value="Morning" />
            <el-option label="Evening" value="Evening" />
            <el-option label="Night" value="Night" />
          </el-select>
        </el-form-item>
        <el-button type="success" @click="submitShift" :disabled="!shiftForm.staff_id || !shiftForm.shift_type">
            {{ isEditing ? 'Save Changes' : 'Confirm' }}
        </el-button>
        <el-button v-if="isEditing" @click="resetForm">Cancel</el-button>
      </el-form>

      <template #footer>
        <el-button @click="detailDialogVisible = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import dayjs from 'dayjs';

const selectedDate = ref(new Date());
const shifts = ref([]);
const staffList = ref([]);
const detailDialogVisible = ref(false);
const shiftLoading = ref(false);
const selectedDay = ref('');

const API_SHIFT = 'http://127.0.0.1:8000/api/shifts/';
const API_STAFF = 'http://127.0.0.1:8000/api/staff/';

const initialForm = {
  id: null,
  shift_date: '',
  staff_id: null,
  shift_type: ''
};

const shiftForm = reactive({...initialForm});

const isEditing = computed(() => !!shiftForm.id);

const shiftsByDate = computed(() => {
  return shifts.value.reduce((acc, shift) => {
    const dateStr = dayjs(shift.shift_date).format('YYYY-MM-DD');
    if (!acc[dateStr]) {
      acc[dateStr] = [];
    }
    acc[dateStr].push(shift);
    return acc;
  }, {});
});

const shiftsForSelectedDay = computed(() => {
  return shiftsByDate.value[selectedDay.value] || [];
});

const today = dayjs().format('YYYY-MM-DD');


// Fetch Data Functions
const fetchShifts = async () => {
  try {
    const response = await axios.get(API_SHIFT);
    shifts.value = response.data;
  } catch (error) {
    ElMessage.error('Failed to load shift data.');
  }
};

const fetchStaffList = async () => {
  try {
    const response = await axios.get(API_STAFF);
    staffList.value = response.data;
  } catch (error) {
    console.error('Error fetching staff list:', error);
  }
};

// Form and Dialog Handlers

const resetForm = () => {
    Object.assign(shiftForm, {...initialForm, shift_date: selectedDay.value});
}

const openDetailDialog = (dateStr) => {
  selectedDay.value = dateStr;
  resetForm();
  detailDialogVisible.value = true;
};

const openShiftForm = (shift) => {
    // Populate form for editing
    Object.assign(shiftForm, {
        id: shift.id,
        shift_date: dayjs(shift.shift_date).format('YYYY-MM-DD'),
        staff_id: shift.staff_id,
        shift_type: shift.shift_type
    });
};


// CRUD Operations
const submitShift = async () => {
  shiftLoading.value = true;
  try {
    if (isEditing.value) {
      // UPDATE (PUT request)
      await axios.put(API_SHIFT + shiftForm.id, {
          staff_id: shiftForm.staff_id,
          shift_date: shiftForm.shift_date,
          shift_type: shiftForm.shift_type
      });
      ElMessage.success('Shift record updated successfully!');
    } else {
      // CREATE (POST request)
      await axios.post(API_SHIFT, shiftForm);
      ElMessage.success('Shift record added successfully!');
    }
    // Refresh data
    fetchShifts();
    resetForm();
  } catch (error) {
    ElMessage.error(`Failed: ${error.response?.data?.detail || error.message}`);
  } finally {
    shiftLoading.value = false;
  }
};

const deleteShift = async (shiftId) => {
  ElMessageBox.confirm(
    'Are you sure you want to delete this shift record?',
    'Warning',
    {
      confirmButtonText: 'Confirm',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  ).then(async () => {
    try {
      // DELETE request
      await axios.delete(API_SHIFT + shiftId);
      ElMessage.success('Shift record deleted successfully.');
      fetchShifts();
    } catch (error) {
      ElMessage.error('Delete failed.');
    }
  }).catch(() => {
    // User cancelled
  });
};

onMounted(() => {
  fetchShifts();
  fetchStaffList();
});

defineExpose({
    fetchShifts
})
</script>

<style scoped>
.calendar-day {
  height: 100%;
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
  position: relative;
}
.calendar-day:hover {
  background-color: #f0f9eb;
}
.shift-count-badge {
    position: absolute;
    bottom: 5px;
    right: 5px;
}
.day-number {
    font-size: 1.1em;
    font-weight: bold;
    margin-bottom: 5px;
}
.shift-form-area {
    padding: 10px 0;
}
</style>