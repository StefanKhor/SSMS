<template>
  <div class="shift-stats-container">
    <h2>Admin Tools</h2>
    
    <el-card class="box-card" style="margin-bottom: 30px;">
      <template #header>
        <div class="card-header">
          <span>Auto Scheduling</span>
        </div>
      </template>
      <el-alert style="margin-bottom: 15px;" title="Warning" type="error" description="Auto scheduling will overwrite and create a automated schedule, please proceed with caution." show-icon :closable="true"/>
      <el-form :model="scheduleForm" label-width="100px" v-loading="scheduling">
        <el-form-item label="Date Range">
            <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="to"
            start-placeholder="Start Date"
            end-placeholder="End Date"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        
        <el-form-item label="Shift">
            <el-checkbox-group v-model="scheduleForm.shift_types">
                <el-checkbox label="Morning">Morning</el-checkbox>
                <el-checkbox label="Evening">Evening</el-checkbox>
                <el-checkbox label="Night">Night</el-checkbox>
            </el-checkbox-group>
            <p v-if="scheduleForm.shift_types.length === 0" style="color: red; margin-top: 5px;">Please select at least one shift!</p>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="warning" 
            :disabled="!dateRange || scheduleForm.shift_types.length === 0"
            @click="triggerAutoSchedule"
          >
            Generate Auto Schedule
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="box-card" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>Export Data</span>
        </div>
      </template>
      <el-button type="success" :loading="exporting" @click="handleExport" style="margin-top: 15px;">
        <el-icon><Download /></el-icon>
        Export Shift Schedule (.xlsx)
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';
import { Download } from '@element-plus/icons-vue'

const exporting = ref(false);
const scheduling = ref(false);

const dateRange = ref(null);
const scheduleForm = reactive({
    start_date: '',
    end_date: '',
    shift_types: ['Morning', 'Evening', 'Night'],
});

const disabledDate = (time) => {
  const today = new Date().setHours(0, 0, 0, 0); 
  return time.getTime() < today;
}

const API_AUTO_SCHEDULE = 'http://127.0.0.1:8000/api/schedule/auto/';
const API_EXPORT = 'http://127.0.0.1:8000/api/schedule/export/';


const emit = defineEmits(['schedule-complete']);

const triggerAutoSchedule = async () => {
    if (!dateRange.value || dateRange.value.length !== 2) {
        ElMessage.warning('Please select a valid date range.');
        return;
    }
    
    // Map the date range model to the request form
    scheduleForm.start_date = dateRange.value[0];
    scheduleForm.end_date = dateRange.value[1];
    
    if (scheduleForm.shift_types.length === 0) {
        ElMessage.warning('Please select at least one shift type.');
        return;
    }

    if (!confirm(`Are you sure you want to generate an auto schedule from ${scheduleForm.start_date} to ${scheduleForm.end_date}?`)) {
        return;
    }

    scheduling.value = true;
    try {
        const response = await axios.post(API_AUTO_SCHEDULE, scheduleForm);
        ElMessage.success(response.data.message);
        
        
    } catch (error) {
        const detail = error.response?.data?.detail || 'Auto scheduling failed. Please try again.';
        ElMessage.error(detail);
    } finally {
        scheduling.value = false;
        emit('schedule-complete');
    }
};

const handleExport = async () => {
  exporting.value = true;
  ElMessage.info('Exporting...');
  try {
    const response = await axios({
      url: API_EXPORT,
      method: 'GET',
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'Shift_Schedule_' + new Date().toISOString().slice(0, 10) + '.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
    ElMessage.success('Export successful!');
  } catch (error) {
    ElMessage.error('Export failed. Please try again.');
    console.error(error);
  } finally {
    exporting.value = false;
  }
};
</script>