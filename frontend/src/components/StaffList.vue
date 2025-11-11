<template>
  <div>
    <el-button type="primary" @click="openDialog(null)">+ New Staff</el-button>
    
    <el-table :data="staffs" style="width: 100%; margin-top: 15px;" border v-loading="loading">
      <el-table-column prop="name" label="Name" width="150" />
      <el-table-column prop="age" label="Age" width="100" />
      <el-table-column prop="position" label="Position" />
      <el-table-column label="Actions" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">Edit</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <StaffForm 
      :visible="dialogVisible" 
      :currentStaff="currentStaff"
      @close="closeDialog" 
      @submit-success="fetchStaffs" 
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import StaffForm from './StaffForm.vue';

const staffs = ref([]);
const dialogVisible = ref(false);
const currentStaff = ref(null);
const loading = ref(false);

const API_BASE = 'http://127.0.0.1:8000/api/staff/';

const fetchStaffs = async () => {
  loading.value = true;
  try {
    const response = await axios.get(API_BASE);
    staffs.value = response.data;
  } catch (error) {
    ElMessage.error('Error fetching staff data.');
    console.error('Error fetching staff:', error);
  } finally {
    loading.value = false;
  }
};

const openDialog = (staff) => {
  currentStaff.value = staff;
  dialogVisible.value = true;
};

const closeDialog = () => {
  dialogVisible.value = false;
  currentStaff.value = null;
};

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this staff member? (This will soft delete the record)')) {
    try {
      await axios.delete(API_BASE + id);
      fetchStaffs();
      ElMessage.success('Staff member has been deleted.');
    } catch (error) {
      ElMessage.error('Failed to delete staff member.');
    }
  }
};

onMounted(fetchStaffs);

defineExpose({
    fetchStaffs
})
</script>