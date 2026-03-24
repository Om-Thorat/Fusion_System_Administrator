import React, { useState, useMemo } from "react";
import {
    Tabs, Card, Text, ScrollArea, Container, Title,
    Flex, Button, TextInput, MultiSelect, Grid, Paper,
    Center, Divider, Checkbox, Group, Modal,
    rem, useMantineColorScheme
} from "@mantine/core";
import { debounce } from "lodash";
import { FaCheck } from "react-icons/fa";
import { showNotification } from "@mantine/notifications";

const STATIC_FACULTY = [
    {
        id: "snsharma",
        username: "snsharma",
        full_name: "Prof. Sanjeev Narayan Sharma",
        user_type: "faculty",
        department: "ECE",
        designations: ["Professor"],
        gender: "M"
    },
    {
        id: "rkverma",
        username: "rkverma",
        full_name: "Dr. Ritu Kumari Verma",
        user_type: "faculty",
        department: "CSE",
        designations: ["Associate Professor"],
        gender: "F"
    },
    {
        id: "ajsingh",
        username: "ajsingh",
        full_name: "Dr. Ajay Singh",
        user_type: "faculty",
        department: "EEE",
        designations: ["Assistant Professor"],
        gender: "M"
    },
    {
        id: "nmathur",
        username: "nmathur",
        full_name: "Prof. Neelam Mathur",
        user_type: "faculty",
        department: "Mathematics",
        designations: ["Professor"],
        gender: "F"
    },
    {
        id: "vkrishnan",
        username: "vkrishnan",
        full_name: "Dr. Vinod Krishnan",
        user_type: "faculty",
        department: "Mechanical",
        designations: ["Assistant Professor"],
        gender: "M"
    },
    {
        id: "sgupta",
        username: "sgupta",
        full_name: "Dr. Swati Gupta",
        user_type: "faculty",
        department: "Civil",
        designations: ["Associate Professor"],
        gender: "F"
    },
    {
        id: "mjain",
        username: "mjain",
        full_name: "Prof. Manish Jain",
        user_type: "faculty",
        department: "CSE",
        designations: ["Professor"],
        gender: "M"
    },
    {
        id: "pkhanna",
        username: "pkhanna",
        full_name: "Dr. Pooja Khanna",
        user_type: "faculty",
        department: "Humanities",
        designations: ["Assistant Professor"],
        gender: "F"
    },
    {
        id: "tbhushan",
        username: "tbhushan",
        full_name: "Prof. Tarun Bhushan",
        user_type: "faculty",
        department: "Physics",
        designations: ["Professor"],
        gender: "M"
    },
    {
        id: "adewan",
        username: "adewan",
        full_name: "Dr. Anjali Dewan",
        user_type: "faculty",
        department: "Chemistry",
        designations: ["Associate Professor"],
        gender: "F"
    }
];

const InfoCard = ({ person, selectable, selected, onSelectChange }) => {
    const { colorScheme } = useMantineColorScheme();
    const isDark = colorScheme === "dark";
    return (
        <Card shadow="sm" radius="xl" withBorder p="lg" style={{
            backgroundColor: isDark ? "#2c2e33" : "#fdfdfd",
            color: isDark ? "#fff" : "#000"
        }}>
            <Group position="apart" align="flex-start">
                <div style={{ flex: 1 }}>
                    <Text fw={600} size="lg" mb="xs" style={{ color: isDark ? "#fff" : "#000" }}>
                        {person.full_name}
                    </Text>
                    <Text size="sm" c="dimmed"><strong>Username:</strong> {person.username}</Text>
                    <Divider my="sm" />
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Department:</strong> {person.department}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Designation:</strong> {person.designations.join(', ')}</Text>
                    <Text size="sm" style={{ color: isDark ? "#ccc" : "#000" }}><strong>Gender:</strong> {person.gender}</Text>
                </div>
                {selectable && (
                    <Checkbox
                        checked={selected}
                        onChange={() => onSelectChange(person.username)}
                        mt="sm"
                    />
                )}
            </Group>
        </Card>
    );
};

const extractUnique = (arr, key) => [...new Set(arr.map(item => String(item[key])))];

const filterAndSearch = (data, filters, searchQuery) =>
    data.filter((person) => {
        const matchSearch = person.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            person.username.toLowerCase().includes(searchQuery.toLowerCase());

        const matchFilters = Object.entries(filters).every(([key, values]) => {
            if (values.length === 0) return true;
            return values.includes(String(person[key]));
        });

        return matchSearch && matchFilters;
    });

const ArchiveFacultyPage = () => {
    const { colorScheme } = useMantineColorScheme();
    const isDark = colorScheme === "dark";
    const checkIcon = <FaCheck style={{ width: rem(20), height: rem(20) }} />;

    const [activeTab, setActiveTab] = useState("archive");
    const [searchQuery, setSearchQuery] = useState("");
    const [filters, setFilters] = useState({
        department: [], designation: [], category: [], gender: []
    });
    const [selectedUsernames, setSelectedUsernames] = useState([]);
    const [modalOpened, setModalOpened] = useState(false);

    const handleSearchChange = useMemo(() =>
        debounce((value) => setSearchQuery(value), 200), []);

    const filteredData = useMemo(() =>
        filterAndSearch(STATIC_FACULTY, filters, searchQuery),
        [filters, searchQuery]);

    const isSelected = (username) => selectedUsernames.includes(username);
    const toggleSelect = (username) => {
        setSelectedUsernames((prev) =>
            prev.includes(username) ? prev.filter(u => u !== username) : [...prev, username]
        );
    };

    const selectAll = () => {
        setSelectedUsernames(filteredData.map(u => u.username));
    };

    const clearSelection = () => setSelectedUsernames([]);

    const handleArchive = () => {
        showNotification({
            icon: checkIcon,
            title: "Success",
            position: "top-center",
            withCloseButton: true,
            autoClose: 5000,
            message: `Archived selected faculty members`,
            color: "green",
        });
        clearSelection();
        setModalOpened(false);
    };

    return (
        <Container size="lg" py="xl" style={{ backgroundColor: isDark ? '#1a1b1e' : '#f7f7f7', minHeight: '100vh' }}>
            <Flex
                direction={{ base: 'column', sm: 'row' }}
                gap={{ base: 'sm', sm: 'lg' }}
                justify={{ sm: 'center' }}
                mb="xl"
            >
                <Button
                    variant="gradient"
                    size="xl"
                    radius="xs"
                    gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                    sx={{ display: 'block', width: { base: '100%', sm: 'auto' }, whiteSpace: 'normal', padding: '1rem', textAlign: 'center' }}
                >
                    <Title order={1} sx={{ fontSize: { base: 'lg', sm: 'xl' }, lineHeight: 1.2, wordBreak: 'break-word' }}>
                        Archive Faculty
                    </Title>
                </Button>
            </Flex>

            <Paper shadow="lg" p="xl" radius="xl" withBorder style={{ backgroundColor: isDark ? '#2c2e33' : '#fff', borderColor: isDark ? '#444' : '#e0e0e0' }}>
                <Tabs value={activeTab} onChange={setActiveTab} variant="pills" color="blue" radius="lg" keepMounted={false}>
                    <Tabs.List grow mb="lg">
                        <Tabs.Tab value="archive">ARCHIVE</Tabs.Tab>
                        <Tabs.Tab value="archived">ARCHIVED</Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="archive">
                        <Grid mb="lg">
                            <Grid.Col span={12}>
                                <TextInput
                                    placeholder="🔍 Search faculty"
                                    radius="md"
                                    onChange={(e) => handleSearchChange(e.currentTarget.value)}
                                />
                            </Grid.Col>
                            {["department", "designation", "category", "gender"].map((key) => (
                                <Grid.Col span={6} key={key}>
                                    <MultiSelect
                                        label={key[0].toUpperCase() + key.slice(1)}
                                        placeholder={`Filter by ${key}`}
                                        value={filters[key]}
                                        onChange={(value) => setFilters((prev) => ({ ...prev, [key]: value }))}
                                        data={extractUnique(STATIC_FACULTY, key)}
                                        radius="md"
                                        searchable
                                        clearable
                                    />
                                </Grid.Col>
                            ))}
                        </Grid>

                        <Group mb="md">
                            <Button onClick={selectAll} variant="light">Select All</Button>
                            <Button onClick={clearSelection} variant="default">Clear Selection</Button>
                        </Group>

                        <ScrollArea h={400}>
                            <Grid>
                                {filteredData.map((faculty) => (
                                    <Grid.Col span={12} key={faculty.username}>
                                        <InfoCard
                                            person={faculty}
                                            selectable
                                            selected={isSelected(faculty.username)}
                                            onSelectChange={toggleSelect}
                                        />
                                    </Grid.Col>
                                ))}
                            </Grid>
                        </ScrollArea>

                        {selectedUsernames.length > 0 && (
                            <Group mt="lg" position="right">
                                <Button color="blue" onClick={() => setModalOpened(true)}>Archive</Button>
                            </Group>
                        )}
                    </Tabs.Panel>

                    <Tabs.Panel value="archived">
                        <Title order={3} mb="md">Recently Archived</Title>
                        <Grid>
                            {STATIC_FACULTY.slice(0, 2).map((s) => (
                                <Grid.Col span={12} key={s.username}>
                                    <InfoCard person={s} />
                                </Grid.Col>
                            ))}
                        </Grid>
                    </Tabs.Panel>
                </Tabs>
            </Paper>

            <Modal
                opened={modalOpened}
                onClose={() => setModalOpened(false)}
                title="Confirm Archive"
            >
                <Text size="sm">Are you sure you want to archive the selected faculty members?</Text>
                <Group position="right" mt="md">
                    <Button variant="outline" onClick={() => setModalOpened(false)}>Cancel</Button>
                    <Button color="blue" onClick={handleArchive}>Confirm</Button>
                </Group>
            </Modal>
        </Container>
    );
};

export default ArchiveFacultyPage;