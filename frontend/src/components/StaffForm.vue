<template>
  <el-dialog 
    :model-value="visible" 
    :title="currentStaff ? 'Edit Staff Information' : 'Add New Staff'" 
    width="400px"
    @close="handleClose"
  >
    <el-form :model="form" label-width="80px" v-loading="loading">
      <el-form-item label="Name" required>
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="Age" required>
        <el-input-number v-model="form.age" :min="18" :max="65" />
      </el-form-item>
      <el-form-item label="Position" required>
        <el-input v-model="form.position" />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">Cancel</el-button>
        <el-button type="primary" @click="submitForm">Submit</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const props = defineProps({
  visible: Boolean,
  currentStaff: Object, 
});

const emit = defineEmits(['close', 'submitSuccess']);

const initialForm = { name: '', age: 25, position: '' };
const form = ref({...initialForm});
const loading = ref(false);

watch(() => props.currentStaff, (newVal) => {
  if (newVal) {
    // Edit mode
    form.value = { 
      name: newVal.name, 
      age: newVal.age, 
      position: newVal.position 
    };
  } else {
    // New mode
    form.value = {...initialForm};
  }
});

const handleClose = () => {
    emit('close');
}

const submitForm = async () => {
  if (!form.value.name || !form.value.position) {
    ElMessage.warning('Please fill in all required fields.');
    return;
  }
  loading.value = true;
  try {
    if (props.currentStaff) {
      await axios.put(`http://127.0.0.1:8000/api/staff/${props.currentStaff.id}`, form.value);
      ElMessage.success('Staff information updated successfully!');
    } else {
      await axios.post('http://127.0.0.1:8000/api/staff/', form.value);
      ElMessage.success('New staff member added successfully!');
    }
    
    emit('submitSuccess'); 
    handleClose();
  } catch (error) {
    ElMessage.error(`Operation failed: ${error.message}`);
  } finally {
    loading.value = false;
  }
};
</script>